"""Enforce the existing canonical basis contract for every SQL writer."""

from django.db import migrations

# Python str.strip whitespace (including the C0 separators), not locale-dependent \s.
_WHITESPACE = [
    *range(9, 14),
    *range(28, 33),
    133,
    160,
    5760,
    *range(8192, 8203),
    8232,
    8233,
    8239,
    8287,
    12288,
]
_TRIM_CHARS = " || ".join(f"chr({code})" for code in _WHITESPACE)

VALIDATORS = r"""
CREATE FUNCTION catalog_values_trim(v text) RETURNS text LANGUAGE sql IMMUTABLE STRICT
AS $$ SELECT btrim(v, __TRIM_CHARS__); $$;

CREATE FUNCTION catalog_values_keys(v jsonb, names text[]) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF v IS NULL OR jsonb_typeof(v) IS DISTINCT FROM 'object' THEN RETURN false; END IF;
    RETURN (v ?& names) AND (SELECT count(*) FROM jsonb_object_keys(v))=cardinality(names);
END; $$;

CREATE FUNCTION catalog_values_horizon_number(v jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE text_value text; number_value numeric;
BEGIN
    IF v IS NULL OR jsonb_typeof(v) IS DISTINCT FROM 'string' THEN RETURN false; END IF;
    text_value := v #>> '{}';
    -- Stored values are canonical output, not the localized transport input.
    IF text_value <> catalog_values_trim(text_value) OR length(text_value)>100
       OR text_value !~ '^(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$' THEN RETURN false; END IF;
    IF position('.' IN text_value)>0
       AND length(split_part(text_value,'.',2))>9 THEN RETURN false; END IF;
    number_value := text_value::numeric;
    RETURN number_value>0 AND number_value<=999999999999999999999999.999999999;
END; $$;

CREATE FUNCTION catalog_values_basis_valid(
    p_kind text, p_status text, p_base text, p_return_type text, b jsonb
) RETURNS boolean LANGUAGE plpgsql STABLE AS $$
DECLARE key text; h jsonb; u jsonb; date_text text; source_text text;
BEGIN
    IF p_kind IS NULL OR p_kind NOT IN ('money','quantity','return')
       OR p_status IS NULL OR p_status NOT IN ('known','unknown','not_applicable')
       OR p_base IS NULL THEN RETURN false; END IF;
    IF b IS NULL OR b='null'::jsonb THEN
        RETURN coalesce(p_kind='money'
            OR (p_kind='quantity' AND p_base NOT IN ('DAY','MONTH','YEAR'))
            OR (p_kind='return' AND p_status IN ('unknown','not_applicable')), false);
    END IF;
    IF p_kind='money' THEN RETURN false; END IF;
    IF p_kind='quantity' THEN
        IF p_base NOT IN ('DAY','MONTH','YEAR') THEN RETURN false; END IF;
        IF NOT catalog_values_keys(b, ARRAY['start_basis']) THEN RETURN false; END IF;
        IF jsonb_typeof(b->'start_basis') IS DISTINCT FROM 'string' THEN RETURN false; END IF;
        source_text := b->>'start_basis';
        RETURN length(source_text) BETWEEN 1 AND 200
            AND source_text=catalog_values_trim(source_text);
    END IF;
    IF NOT catalog_values_keys(b, ARRAY['version','metric_type','period','horizon',
        'basis_date','price_basis','scope','observation','source']) THEN RETURN false; END IF;
    IF jsonb_typeof(b->'version') IS DISTINCT FROM 'number'
        OR b->>'version' IS DISTINCT FROM '1' THEN RETURN false; END IF;
    FOREACH key IN ARRAY ARRAY['metric_type','period','basis_date','price_basis',
        'scope','observation','source'] LOOP
        IF jsonb_typeof(b->key) IS DISTINCT FROM 'string' THEN RETURN false; END IF;
    END LOOP;
    IF b->>'metric_type' NOT IN ('irr','simple_rate','effective_rate')
        OR b->>'metric_type' IS DISTINCT FROM p_return_type
        OR b->>'period' NOT IN ('annual','monthly','total')
        OR b->>'price_basis' NOT IN ('nominal','real')
        OR b->>'scope' NOT IN ('project','investor')
        OR b->>'observation' NOT IN ('forecast','observed','claimed') THEN RETURN false; END IF;
    source_text := b->>'source';
    IF length(source_text)>2000 OR catalog_values_trim(source_text)='' THEN RETURN false; END IF;
    date_text := b->>'basis_date';
    IF length(date_text)<>10 OR date_text !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        THEN RETURN false; END IF;
    BEGIN
        PERFORM date_text::date;
    EXCEPTION WHEN invalid_datetime_format OR datetime_field_overflow THEN
        RETURN false;
    END;
    h := b->'horizon';
    IF NOT catalog_values_keys(h, ARRAY['value','unit']) THEN RETURN false; END IF;
    IF NOT catalog_values_horizon_number(h->'value') THEN RETURN false; END IF;
    u := h->'unit';
    IF NOT catalog_values_keys(u, ARRAY['code','version']) THEN RETURN false; END IF;
    IF jsonb_typeof(u->'code') IS DISTINCT FROM 'string'
        OR jsonb_typeof(u->'version') IS DISTINCT FROM 'number' THEN RETURN false; END IF;
    IF u->>'code' NOT IN ('DAY','MONTH','YEAR')
        OR u->>'version' !~ '^[1-9][0-9]{0,3}$' THEN RETURN false; END IF;
    RETURN EXISTS(SELECT 1 FROM catalog_unitdefinition
        WHERE code=u->>'code' AND version=(u->>'version')::integer AND kind='quantity');
END; $$;
""".replace("__TRIM_CHARS__", _TRIM_CHARS)

PREFLIGHT = """
DO $$
DECLARE row_data record; table_name text; kind_name text; bad boolean;
BEGIN
    FOR table_name, kind_name IN SELECT * FROM (VALUES
        ('catalog_moneyvalue','money'), ('catalog_quantity','quantity'),
        ('catalog_returnmetric','return')) AS targets(table_name,kind_name) LOOP
        EXECUTE format('SELECT EXISTS(SELECT 1 FROM %I v '
            'LEFT JOIN catalog_fielddefinition d ON d.id=v.definition_id '
            'LEFT JOIN catalog_unitdefinition u ON u.id=v.unit_id '
            'WHERE catalog_values_basis_valid($1,v.status,u.base_code,d.return_type,v.basis) '
            'IS NOT TRUE)', table_name) INTO bad USING kind_name;
        IF bad THEN
            RAISE EXCEPTION 'Existing incompatible basis in %; audit required, no data changed',
                table_name USING ERRCODE='23514';
        END IF;
    END LOOP;
END; $$;
"""

GUARDS = """
CREATE FUNCTION catalog_values_basis_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE unit_base text; metric_type text;
BEGIN
    SELECT base_code INTO unit_base FROM catalog_unitdefinition WHERE id=NEW.unit_id;
    SELECT return_type INTO metric_type FROM catalog_fielddefinition WHERE id=NEW.definition_id;
    IF catalog_values_basis_valid(TG_ARGV[0],NEW.status,unit_base,metric_type,NEW.basis)
        IS NOT TRUE THEN
        RAISE EXCEPTION 'Invalid basis for versioned catalog value' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER money_basis_guard BEFORE INSERT OR UPDATE ON catalog_moneyvalue
FOR EACH ROW EXECUTE FUNCTION catalog_values_basis_guard('money');
CREATE TRIGGER quantity_basis_guard BEFORE INSERT OR UPDATE ON catalog_quantity
FOR EACH ROW EXECUTE FUNCTION catalog_values_basis_guard('quantity');
CREATE TRIGGER return_basis_guard BEFORE INSERT OR UPDATE ON catalog_returnmetric
FOR EACH ROW EXECUTE FUNCTION catalog_values_basis_guard('return');
"""

REVERSE_GUARDS = """
DROP TRIGGER return_basis_guard ON catalog_returnmetric;
DROP TRIGGER quantity_basis_guard ON catalog_quantity;
DROP TRIGGER money_basis_guard ON catalog_moneyvalue;
DROP FUNCTION catalog_values_basis_guard();
"""
REVERSE_VALIDATORS = """
DROP FUNCTION catalog_values_basis_valid(text,text,text,text,jsonb);
DROP FUNCTION catalog_values_horizon_number(jsonb);
DROP FUNCTION catalog_values_keys(jsonb,text[]);
DROP FUNCTION catalog_values_trim(text);
"""


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_value_definitions")]
    operations = [
        migrations.RunSQL(VALIDATORS, REVERSE_VALIDATORS),
        migrations.RunSQL(PREFLIGHT, migrations.RunSQL.noop),
        migrations.RunSQL(GUARDS, REVERSE_GUARDS),
    ]
