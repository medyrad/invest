"use client";
import {useState} from "react";
import {Button} from "@/components/ui/button";
import {Checkbox} from "@/components/ui/checkbox";
import {Popover,PopoverContent,PopoverTrigger} from "@/components/ui/popover";
import {ArrowDown2} from "@/components/iconsax";
import {cn,faNumber} from "@/lib/utils";
// Presentation port of the same-hash reference engine MultiDrop; no reference runtime.
export function MultiDrop({ items, onToggle, single }: { items: { key: string; checked: boolean; disabled: boolean; title: string; hint?: string }[]; onToggle: (key: string) => void; single?: boolean }) {
  const [open, setOpen] = useState(false);
  const on = items.filter((i) => i.checked);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" role="combobox" aria-expanded={open} className="h-auto min-h-12 w-full justify-between gap-3 whitespace-normal rounded-2xl bg-white px-4 py-2 text-right shadow-none hover:bg-white">
          <span className={cn("flex min-w-0 flex-wrap gap-1.5 text-sm", on.length ? "font-bold text-ink" : "font-semibold text-muted-foreground")}>
            {on.length ? on.map((i) => <span key={i.key} className="rounded-full bg-ink/[0.06] px-2.5 py-0.5 text-[12px] font-extrabold text-primary-ink">{i.title}</span>) : "انتخاب کنید"}
          </span>
          <span className="flex shrink-0 items-center gap-2 text-xs font-bold text-muted-foreground">{!single && on.length > 0 && `${faNumber(on.length)} از ${faNumber(items.length)}`}<ArrowDown2 size={16} className={cn("transition-transform", open && "rotate-180")} /></span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="thin-scroll max-h-80 w-(--radix-popover-trigger-width) overflow-y-auto rounded-2xl p-1.5">
        {items.map((i) => (
          <label key={i.key} className={cn("flex cursor-pointer items-start gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-ink/[0.03]", i.checked && "bg-ink/[0.04]")}>
            <Checkbox role={single ? "radio" : undefined} checked={i.checked} disabled={i.disabled} onCheckedChange={() => { if (single && i.checked) return; onToggle(i.key); if (single) setOpen(false); }} className={cn("mt-0.5 size-5 border-pine/25 bg-white", single ? "rounded-full" : "rounded-md")} />
            <span className="min-w-0"><span className="block text-sm font-bold leading-6 text-ink">{i.title}</span>{i.hint && <span className="block text-xs leading-5 text-muted-foreground">{i.hint}</span>}</span>
          </label>
        ))}
      </PopoverContent>
    </Popover>
  );
}
