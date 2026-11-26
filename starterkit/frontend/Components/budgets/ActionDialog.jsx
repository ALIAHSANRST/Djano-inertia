import { Button } from "@/Components/ui/button"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/Components/ui/dialog"

export function ActionDialog({
  title, description, onClose, onSubmit, processing, error, submitLabel, destructive, children,
}) {
  return (
    <Dialog open onOpenChange={(open) => { if (!open && !processing) onClose() }}>
      <DialogContent>
        <form onSubmit={onSubmit} className="grid gap-4">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          {children}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={processing}>Cancel</Button>
            <Button type="submit" variant={destructive ? "destructive" : "default"} disabled={processing}>
              {processing ? "Saving…" : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
