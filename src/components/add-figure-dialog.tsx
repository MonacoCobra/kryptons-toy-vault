import { useState } from "react";
import { toast } from "sonner";
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
import { CONDITIONS, useVault } from "@/lib/store";
import type { CatalogFigure, Condition } from "@/lib/types";

export function AddFigureDialog({
  figure,
  open,
  onOpenChange,
}: {
  figure: CatalogFigure;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const existing = useVault((s) => s.ownedFigures[figure.id]);
  const addFigure = useVault((s) => s.addFigure);
  const updateFigure = useVault((s) => s.updateFigure);
  const [acquiredDate, setAcquiredDate] = useState(existing?.acquiredDate ?? new Date().toISOString().slice(0, 10));
  const [acquiredPrice, setAcquiredPrice] = useState(existing?.acquiredPrice?.toString() ?? figure.msrp.toString());
  const [condition, setCondition] = useState<Condition>(existing?.condition ?? "mib");
  const [notes, setNotes] = useState(existing?.notes ?? "");
  const [photo, setPhoto] = useState(existing?.photoDataUrl);

  async function onFile(file?: File) {
    if (!file) return;
    try {
      const data = await compressImage(file);
      setPhoto(data);
    } catch {
      toast.error("Could not read that photo.");
    }
  }

  function save() {
    const payload = {
      figureId: figure.id,
      acquiredDate,
      acquiredPrice: acquiredPrice ? Number(acquiredPrice) : undefined,
      condition,
      notes: notes.trim() || undefined,
      photoDataUrl: photo,
    };
    if (existing) updateFigure(figure.id, payload);
    else addFigure(payload);
    toast.success(existing ? "Vault entry updated." : "Added to the vault.");
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{existing ? "Update vault entry" : "Add to vault"}</DialogTitle>
          <DialogDescription>
            {figure.line} · {figure.name}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="acq-date">Acquisition date</Label>
            <Input id="acq-date" type="date" value={acquiredDate} onChange={(e) => setAcquiredDate(e.target.value)} />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="acq-price">Acquisition price (USD)</Label>
            <Input
              id="acq-price"
              type="number"
              min="0"
              step="0.01"
              value={acquiredPrice}
              onChange={(e) => setAcquiredPrice(e.target.value)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label>Condition</Label>
            <Select value={condition} onValueChange={(v) => setCondition(v as Condition)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONDITIONS.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="photo">Your photo</Label>
            <Input id="photo" type="file" accept="image/*" onChange={(e) => onFile(e.target.files?.[0])} />
            {photo ? <img src={photo} alt="" className="mt-1 h-28 w-full rounded-sm object-cover" /> : null}
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="notes">Notes</Label>
            <Textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Carded, missing extra, shelf wear…" />
          </div>
          <Button onClick={save}>{existing ? "Save changes" : "Add to vault"}</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
