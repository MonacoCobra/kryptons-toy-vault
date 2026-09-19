import { useEffect, useState } from "react";
import { toast } from "sonner";
import { comicLabel } from "@/data/comics";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { compressImage } from "@/lib/image";
import { GRADES, useVault } from "@/lib/store";
import type { CatalogComic, ComicGrade, CustomComic } from "@/lib/types";

export function AddComicDialog({
  comic,
  custom,
  photo: initialPhoto,
  open,
  onOpenChange,
  onSaved,
  confirmLabel,
}: {
  comic?: CatalogComic;
  custom?: CustomComic;
  photo?: string;
  open: boolean;
  onOpenChange: (v: boolean) => void;
  /** Fired after a successful add/update with owned id + catalog/custom id. */
  onSaved?: (info: { ownedId: string; catalogId?: string; customId?: string }) => void;
  /** Override primary button label (e.g. "Add to collection"). */
  confirmLabel?: string;
}) {
  const ownedComics = useVault((s) => s.ownedComics);
  const existing = comic ? Object.values(ownedComics).find((o) => o.catalogId === comic.id) : undefined;
  const addComic = useVault((s) => s.addComic);
  const updateComic = useVault((s) => s.updateComic);
  const addCustomComic = useVault((s) => s.addCustomComic);

  const label = comic ? comicLabel(comic) : custom ? comicLabel(custom) : "Custom issue";
  const [acquiredDate, setAcquiredDate] = useState(existing?.acquiredDate ?? new Date().toISOString().slice(0, 10));
  const [acquiredPrice, setAcquiredPrice] = useState(
    existing?.acquiredPrice?.toString() ?? (comic?.msrp ?? custom?.msrp ?? 4.99).toString(),
  );
  const [grade, setGrade] = useState<ComicGrade>(existing?.grade ?? "raw");
  const [notes, setNotes] = useState(existing?.notes ?? "");
  const [photo, setPhoto] = useState(existing?.photoDataUrl ?? initialPhoto);

  useEffect(() => {
    if (!open) return;
    setAcquiredDate(existing?.acquiredDate ?? new Date().toISOString().slice(0, 10));
    setAcquiredPrice(
      existing?.acquiredPrice?.toString() ?? (comic?.msrp ?? custom?.msrp ?? 4.99).toString(),
    );
    setGrade(existing?.grade ?? "raw");
    setNotes(existing?.notes ?? "");
    setPhoto(existing?.photoDataUrl ?? initialPhoto);
  }, [open, comic?.id, custom?.id, existing?.id, existing?.acquiredDate, existing?.acquiredPrice, existing?.grade, existing?.notes, existing?.photoDataUrl, comic?.msrp, custom?.msrp, initialPhoto]);

  async function onFile(file?: File) {
    if (!file) return;
    try {
      setPhoto(await compressImage(file));
    } catch {
      toast.error("Could not read that photo.");
    }
  }

  function save() {
    let ownedId = existing?.id ?? "";
    let catalogId = comic?.id;
    let customId = custom?.id;

    if (existing) {
      updateComic(existing.id, {
        acquiredDate,
        acquiredPrice: acquiredPrice ? Number(acquiredPrice) : undefined,
        grade,
        notes: notes.trim() || undefined,
        photoDataUrl: photo,
      });
      ownedId = existing.id;
    } else if (comic) {
      ownedId = addComic({
        catalogId: comic.id,
        acquiredDate,
        acquiredPrice: acquiredPrice ? Number(acquiredPrice) : undefined,
        grade,
        notes: notes.trim() || undefined,
        photoDataUrl: photo,
      });
      catalogId = comic.id;
    } else if (custom) {
      addCustomComic(custom);
      ownedId = addComic({
        catalogId: undefined,
        custom,
        acquiredDate,
        acquiredPrice: acquiredPrice ? Number(acquiredPrice) : undefined,
        grade,
        notes: notes.trim() || undefined,
        photoDataUrl: photo,
      });
      customId = custom.id;
    }
    toast.success(existing ? "Issue updated." : "Issue added to the vault.");
    if (ownedId) onSaved?.({ ownedId, catalogId, customId });
    onOpenChange(false);
  }

  const primary =
    confirmLabel ?? (existing ? "Save changes" : "Add to vault");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        data-testid="add-comic-dialog"
        onOpenAutoFocus={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{existing ? "Update issue" : "Add to collection"}</DialogTitle>
          <DialogDescription>{label}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="c-date">Acquisition date</Label>
            <Input id="c-date" type="date" value={acquiredDate} onChange={(e) => setAcquiredDate(e.target.value)} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-price">Acquisition price (USD)</Label>
            <Input
              id="c-price"
              type="number"
              min="0"
              step="0.01"
              value={acquiredPrice}
              onChange={(e) => setAcquiredPrice(e.target.value)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label>Grade</Label>
            <Select value={grade} onValueChange={(v) => setGrade(v as ComicGrade)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {GRADES.map((g) => (
                  <SelectItem key={g.id} value={g.id}>
                    {g.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-photo">Cover / collection photo</Label>
            <Input id="c-photo" type="file" accept="image/*" onChange={(e) => onFile(e.target.files?.[0])} />
            {photo ? <img src={photo} alt="" className="mt-1 h-36 w-full rounded-sm object-cover" /> : null}
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="c-notes">Notes</Label>
            <Textarea id="c-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Print, defects, CGC cert…" />
          </div>
          <Button
            data-testid="add-comic-confirm"
            onClick={save}
            className="sticky bottom-0 min-h-11 w-full"
          >
            {primary}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
