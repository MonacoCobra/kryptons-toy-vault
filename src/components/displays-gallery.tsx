import { useMemo, useRef, useState, type ChangeEvent } from "react";
import { Camera, ImagePlus, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { compressImage } from "@/lib/image";
import { useVault } from "@/lib/store";
import type { DisplayPhoto } from "@/lib/types";

export function DisplaysGallery() {
  const displays = useVault((s) => s.displays ?? {});
  const addDisplay = useVault((s) => s.addDisplay);
  const updateDisplay = useVault((s) => s.updateDisplay);
  const removeDisplay = useVault((s) => s.removeDisplay);

  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState<{ photoDataUrl: string; title: string; caption: string } | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

  const items = useMemo(
    () => Object.values(displays).sort((a, b) => (a.addedAt < b.addedAt ? 1 : -1)),
    [displays],
  );

  async function onFile(file: File) {
    setBusy(true);
    try {
      const photoDataUrl = await compressImage(file, 1280, 0.78);
      setDraft({ photoDataUrl, title: "", caption: "" });
      setEditingId(null);
    } catch {
      toast.error("Could not read that photo.");
    } finally {
      setBusy(false);
    }
  }

  function handlePick(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) void onFile(file);
  }

  function saveDraft() {
    if (!draft) return;
    if (editingId) {
      updateDisplay(editingId, {
        photoDataUrl: draft.photoDataUrl,
        title: draft.title.trim() || undefined,
        caption: draft.caption.trim() || undefined,
      });
      toast.success("Display updated.");
    } else {
      addDisplay({
        photoDataUrl: draft.photoDataUrl,
        title: draft.title.trim() || undefined,
        caption: draft.caption.trim() || undefined,
      });
      toast.success("Display photo added.");
    }
    setDraft(null);
    setEditingId(null);
  }

  function startEdit(photo: DisplayPhoto) {
    setEditingId(photo.id);
    setDraft({
      photoDataUrl: photo.photoDataUrl,
      title: photo.title ?? "",
      caption: photo.caption ?? "",
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <Button type="button" disabled={busy} onClick={() => cameraRef.current?.click()} className="w-full">
          <Camera className="size-4" />
          Take photo
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={busy}
          onClick={() => galleryRef.current?.click()}
          className="w-full"
        >
          <ImagePlus className="size-4" />
          Choose from gallery
        </Button>
      </div>

      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handlePick}
      />
      <input ref={galleryRef} type="file" accept="image/*" className="hidden" onChange={handlePick} />

      {busy ? (
        <p className="flex items-center justify-center gap-2 text-sm text-muted">
          <Loader2 className="size-4 animate-spin text-gold" />
          Preparing photo…
        </p>
      ) : null}

      {draft ? (
        <div className="rounded-xl bg-bg-elevated p-4 shadow-[var(--shadow-border)]">
          <img
            src={draft.photoDataUrl}
            alt={draft.title || "Display draft"}
            className="mx-auto max-h-72 w-full rounded-sm object-contain"
          />
          <div className="mt-4 grid gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="display-title">Title (optional)</Label>
              <Input
                id="display-title"
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                placeholder="Living room shelf, MCU wall…"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="display-caption">Caption (optional)</Label>
              <Textarea
                id="display-caption"
                value={draft.caption}
                onChange={(e) => setDraft({ ...draft, caption: e.target.value })}
                placeholder="Notes about this setup…"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={saveDraft}>{editingId ? "Save changes" : "Add to Displays"}</Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setDraft(null);
                  setEditingId(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {items.length === 0 && !draft ? (
        <div className="rounded-xl bg-bg-elevated p-10 text-center shadow-[var(--shadow-border)]">
          <p className="font-display text-xl tracking-wide uppercase">No display photos yet</p>
          <p className="mt-2 text-sm text-muted">
            Snap your shelves or upload existing photos to keep a visual inventory of your setups.
          </p>
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((photo) => (
            <li
              key={photo.id}
              className="overflow-hidden rounded-xl bg-bg-elevated shadow-[var(--shadow-border)]"
            >
              <button type="button" className="block w-full" onClick={() => startEdit(photo)}>
                <img
                  src={photo.photoDataUrl}
                  alt={photo.title || "Display"}
                  className="aspect-4/3 w-full object-cover"
                />
              </button>
              <div className="flex items-start justify-between gap-2 p-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{photo.title || "Untitled display"}</p>
                  {photo.caption ? (
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted">{photo.caption}</p>
                  ) : null}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Delete display photo"
                  onClick={() => {
                    removeDisplay(photo.id);
                    toast.success("Display photo removed.");
                  }}
                >
                  <Trash2 className="size-4 text-loss" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
