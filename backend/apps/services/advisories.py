"""Native, versioned reference advisory rules; no script execution or DOM dependency."""

import copy
import json
from pathlib import Path

from apps.workspace.schema import Fault

_DATA = json.loads(Path(__file__).with_name("advisories.json").read_text())
CONFIGS = {c["id"]: c for c in _DATA["configs"]}
TEXT = json.loads(Path(__file__).with_name("guidance-text.json").read_text())
VERSION = 1


def config(key):
    if not isinstance(key, str) or key not in CONFIGS:
        raise Fault("پیکربندی تخصصی شناخته‌شده انتخاب کنید.", field="config")
    return CONFIGS[key]


def questions(key, answers, *, all_fields=False, role="investor"):
    c = config(key)
    if not isinstance(answers, dict):
        raise Fault("پاسخ پرسش‌ها باید یک مجموعه نام‌دار باشد.", field="answers")
    common = {"phase", "owner", "participation", "rehab"}
    return [
        copy.deepcopy(q)
        for q in c["questions"]
        if (role == "investor" or q["id"] not in common)
        and (
            all_fields
            or (
                all(answers.get(k) in vs for k, vs in q.get("active_when", {}).items())
                and not any(answers.get(k) in vs for k, vs in q.get("active_unless", {}).items())
            )
        )
    ]


def evaluate(key, answers, funding="own", role="investor"):
    c = config(key)
    if role not in ["investor", "operator", "contractor", "context"] or funding not in [
        "own",
        "bank",
        "partner",
        "mixed",
        "unknown",
    ]:
        raise Fault("نقش یا منبع تامین معتبر انتخاب کنید.", field="role")
    if not isinstance(answers, dict) or len(answers) > 100:
        raise Fault("پاسخ پرسش‌ها معتبر نیست.", field="answers")
    universe = {q["id"]: q for q in questions(key, {}, all_fields=True)}
    if set(answers) - universe.keys():
        raise Fault("پرسش ناشناخته است.", field="answers")
    for k, v in answers.items():
        if not isinstance(v, str) or v not in [o["value"] for o in universe[k]["options"]]:
            raise Fault("گزینه معتبر پرسش را انتخاب کنید.", field="answers." + k)
    qs = questions(key, answers, role=role)
    a = {q["id"]: answers[q["id"]] for q in qs if q["id"] in answers}
    blocks = [q for q in qs if a.get(q["id"]) in q.get("block", [])]
    decisions = []
    for q in qs:
        value = a.get(q["id"])
        effect = q.get("actions", {}).get(value)
        if effect:
            decisions.append(
                {
                    "question": q["label"],
                    "answer": label(q, value, ""),
                    "effect": effect,
                    "blocking": value in q.get("block", []),
                    "review": value in q.get("review", []),
                }
            )
    if role == "investor":
        guidance = _guidance(c, a, qs, blocks, decisions, funding)
    else:
        guidance = {
            "title": "بررسی تخصصی " + c["name"],
            "models": [],
            "why": c.get("context", ""),
            "checks": list(dict.fromkeys(c["baseChecks"] + [d["effect"] for d in decisions])),
            "next": "شرح خدمت و حدود اختیار را برای بررسی کارشناس مستند کنید.",
            "finance": [],
            "revenue": next(
                (label(q, a.get("revenue")) for q in qs if q["id"] == "revenue"), "تعیین نشده"
            ),
            "answers": [{"question": q["label"], "answer": label(q, a.get(q["id"]))} for q in qs],
        }
    return {
        "config": key,
        "version": VERSION,
        "questions": qs,
        "effective_answers": a,
        "missing": [q["id"] for q in qs if q["id"] not in a],
        "blocked_question_ids": [q["id"] for q in blocks],
        "assessment_blocked": bool(blocks),
        "expert_request_allowed": True,
        "guidance": guidance,
    }


def label(q, value, fallback="تعیین نشده"):
    return next((o["label"] for o in q["options"] if o["value"] == value), fallback)


def _guidance(c, a, qs, blocks, decisions, funding):
    group, typ = c["group"], c["id"]
    building, land = group == "building", group == "landhousing"
    text = TEXT[
        "buildBuildingGuidance"
        if building
        else "buildLandHousingGuidance"
        if land
        else "buildSectorGuidance"
    ]
    out = copy.deepcopy(text["defaults"])
    out["checks"] = list(c["baseChecks"])
    out["finance"] = []
    phase, revenue, owner, rehab = (a.get(k) for k in ["phase", "revenue", "owner", "rehab"])
    context = {
        "b.type === 'lhstudy'": typ == "lhstudy",
        "social": typ in ["flood", "streets", "fire", "ruralroad", "natural", "protection"],
        "a.demand === 'ready'": a.get("demand") == "ready",
        "a.equipment === 'ready'": a.get("equipment") == "ready",
    }

    def resolve(value):
        if isinstance(value, dict) and "test" in value:
            return resolve(value["yes"] if context[value["test"]] else value["no"])
        if isinstance(value, list):
            return [resolve(v) for v in value]
        return value

    def apply(condition):
        rule = text["rules"].get(condition, {})
        out.update({k: resolve(v) for k, v in rule.get("set", {}).items()})
        for k, values in rule.get("append", {}).items():
            out.setdefault(k, []).extend(resolve(values))

    if blocks and not building:
        apply("blocks.length" if land else "blocked.length")
        if not land:
            out["why"] = (
                "بر اساس پاسخ شما، در «"
                + "، ".join(q["label"] for q in blocks)
                + (
                    "» منع یا مخالفت صریح وجود دارد. نوع قرارداد و سر"
                    "مایه بیشتر، این مانع را برطرف نمی\u200cکند."
                )
            )
    elif revenue == "support":
        apply("a.revenue === 'support'")
    elif phase == "existing" and rehab == "no" and not land:
        apply("a.phase === 'existing' && a.rehab === 'no'")
    elif revenue == "saving" and not building and not land:
        apply("a.revenue === 'saving'")
    elif (
        revenue in ["sale", "mixed"]
        if building
        else revenue == "sale" or revenue == "mixed" and group == "land"
    ) and not land:
        apply(
            "a.revenue === 'sale' || a.revenue === 'mixed'"
            if building
            else "a.revenue === 'sale' || (a.revenue === 'mixed' && b.group === 'land')"
        )
    elif revenue == "public":
        apply("a.revenue === 'public'")
    elif land and revenue in ["sale", "mixed"]:
        apply("a.revenue === '" + revenue + "'")
    elif not land and phase == "existing" and rehab == "yes" and owner != "private":
        apply("a.phase === 'existing' && a.rehab === 'yes' && a.owner !== 'private'")
    elif owner == "private" and not land:
        apply("a.owner === 'private'")
        if not building and group in ["industry", "energy", "agriculture", "digital"]:
            apply("['industry', 'energy', 'agriculture', 'digital'].includes(b.group)")
    else:
        apply("else")

    if land:
        out["checks"].extend(d["effect"] for d in decisions)
        if funding != "own":
            apply("b.funding !== 'own'")
        apply("default")
        if not blocks and any(d["review"] for d in decisions):
            out["next"] = (
                next(d["effect"] for d in decisions if d["review"])
                + "، سپس بودجه، زمان و ساختار قرارداد بازبینی شوند."
            )
        out["finance"] = (
            [
                "منابع عمومی یا حمایتی قابل تخصیص و مستند",
                "بودجه نگهداری و تکمیل خدمات، بدون فرض بازده تجاری",
            ]
            if revenue == "support"
            else [
                "آورده نقدی شرکا یا پرداخت کارفرما مطابق قرارداد معتبر",
                "آورده غیرنقدی فقط پس از احراز حق و ارزش‌گذاری",
                "تسهیلات احتمالی پس از احراز پذیرش نهاد مالی و توان بازپرداخت",
            ]
        )
    else:
        if building:
            if phase == "existing" and rehab == "yes" and revenue == "public":
                apply("a.phase === 'existing' && a.rehab === 'yes' && a.revenue === 'public'")
            if phase == "unfinished":
                apply("a.phase === 'unfinished'")
                if revenue not in ["public", "sale", "mixed", "support"]:
                    apply(
                        "a.revenue !== 'public' && !['sale', 'mixed', 'su"
                        "pport'].includes(a.revenue)"
                    )
        else:
            if not blocks and revenue != "support" and phase == "unfinished":
                apply("!blocked.length && a.revenue !== 'support' && a.phase === 'unfinished'")
                if revenue not in ["sale", "mixed", "public", "saving"]:
                    apply("!['sale', 'mixed', 'public', 'saving'].includes(a.revenue)")
            if not blocks and revenue == "public" and phase == "existing" and rehab == "yes":
                apply(
                    "!blocked.length && a.revenue === 'public' && a.p"
                    "hase === 'existing' && a.rehab === 'yes'"
                )
        if phase == "any":
            apply("a.phase === 'any'")
        if owner == "any":
            apply("a.owner === 'any'")
        if building:
            # Explicit native predicates, in the same order as the reference.
            predicates = [
                (a.get("participation") == v, "a.participation === '" + v + "'")
                for v in ["finance", "develop", "operate"]
            ]
            predicates += [
                (a.get("presale") == v, "a.presale === '" + v + "'") for v in ["yes", "unknown"]
            ]
            predicates += [
                (a.get("market") == v, "a.market === '" + v + "'")
                for v in ["premium", "economic", "any"]
            ]
            predicates += [
                (
                    a.get("operator") in ["partner", "unknown"],
                    "a.operator === 'partner' || a.operator === 'unknown'",
                ),
                (
                    a.get("operator") == "ready" or a.get("license") == "ready",
                    "a.operator === 'ready' || a.license === 'ready'",
                ),
                (
                    a.get("license") in ["pending", "unknown"],
                    "a.license === 'pending' || a.license === 'unknown'",
                ),
                (
                    bool(a.get("anchor")) and a["anchor"] != "signed",
                    "a.anchor && a.anchor !== 'signed'",
                ),
                (a.get("anchor") == "signed", "a.anchor === 'signed'"),
                (bool(a.get("commitment") or a.get("buyer")), "a.commitment || a.buyer"),
                (bool(a.get("demand")), "a.demand"),
                (bool(a.get("equipment")), "a.equipment"),
                (
                    a.get("heritage") in ["yes", "unknown"],
                    "a.heritage === 'yes' || a.heritage === 'unknown'",
                ),
            ]
            for valid, condition in predicates:
                if valid:
                    apply(condition)
            if a.get("facility"):
                q = next(q for q in qs if q["id"] == "facility")
                out["checks"].append(
                    "تطبیق الزامات فنی، ظرفیت و مجوزهای "
                    + label(q, a["facility"])
                    + " با اسناد پروژه"
                )
            if funding != "own":
                apply("b.funding !== 'own'")
            if rehab == "unknown":
                apply("a.rehab === 'unknown'")
            out["finance"] = (
                ["کمک و آورده حمایتیِ مشخص و قابل تعهد", "پیش‌بینی بودجه پایدار نگهداری و خدمت"]
                if revenue == "support"
                else [
                    "آورده نقدی سرمایه‌گذار و شریک، آورده غیرنقدی فقط پس از ارزش‌گذاری و پذیرش",
                    (
                        "تسهیلات احتمالی پس از اعتبارسنجی و بررسی توان با"
                        "زپرداخت، در محاسبه سرمایه نقدی منظور نشده"
                    ),
                ]
            )
        else:
            participation = {
                "finance": "معرفی و ارزیابی شریک تخصصی اجرا و بهره‌برداری و حقوق نظارت سرمایه‌گذار",
                "develop": "احراز توان مدیریت اجرا، برنامه هزینه و زمان و تضمین تعهدات",
                "operate": "احراز مجوز و توان بهره‌برداری تخصصی و بودجه نگهداری و سرمایه در گردش",
            }
            if a.get("participation") in participation:
                out["checks"].append(participation[a["participation"]])
            out["checks"].extend(d["effect"] for d in decisions)
            if not blocks and revenue != "support" and any(d["review"] for d in decisions):
                out["next"] = (
                    next(d["effect"] for d in decisions if d["review"])
                    + "، سپس مدل مالی و ساختار ورود دوباره بررسی شود."
                )
            if funding != "own":
                apply("b.funding !== 'own'")
                if not blocks:
                    apply("!blocked.length")
            if rehab == "unknown":
                apply("a.rehab === 'unknown'")
            if group == "heritage":
                apply("b.group === 'heritage'")
                if not blocks and revenue not in ["public", "support"] and rehab != "no":
                    apply(
                        "!blocked.length && a.revenue !== 'public' && a.r"
                        "evenue !== 'support' && a.rehab !== 'no'"
                    )
            out["finance"] = (
                [
                    "آورده حمایتی یا کمک قابل تعهد و مستند",
                    "منبع پایدار هزینه نگهداری و پایش، بدون فرض بازپرداخت تجاری",
                ]
                if revenue == "support"
                else [
                    "آورده نقدی شرکا، آورده غیرنقدی پس از احراز حق، پذیرش و ارزش‌گذاری",
                    (
                        "بدهی / تسهیلات احتمالی پس از احراز صلاحیت و توان"
                        " بازپرداخت، بدون احتساب منابع تاییدنشده"
                    ),
                ]
            )
            if revenue == "saving":
                out["finance"].append(
                    "سرمایه اجرای بهینه‌سازی، بازپرداخت فقط از محل صرفه‌جویی نقدیِ قابل تسویه"
                )
    out["title"] = ("مسیر قابل بررسی برای پروژه " if building else "مسیر قابل بررسی برای ") + c[
        "name"
    ]
    out["revenue"] = next((label(q, revenue) for q in qs if q["id"] == "revenue"), "تعیین نشده")
    out["answers"] = [{"question": q["label"], "answer": label(q, a.get(q["id"]))} for q in qs]
    out["checks"] = list(dict.fromkeys(out["checks"]))
    if not building:
        out.update(decisions=decisions, blocked=bool(blocks))
    return out
