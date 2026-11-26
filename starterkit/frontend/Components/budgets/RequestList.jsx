import { Link } from "@inertiajs/react"
import { Badge } from "@/Components/ui/badge"
import { Button } from "@/Components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/Components/ui/card"

const statusVariants = { Approved: "default", Pending: "outline", Rejected: "destructive", Withdrawn: "secondary" }

export function RequestList({ collection, empty, pageHref, actions }) {
  if (!collection.items.length) return <p className="text-sm text-muted-foreground">{empty}</p>

  return (
    <div className="grid gap-3">
      {collection.items.map((request) => (
        <Card key={request.id}>
          <CardHeader className="gap-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle className="break-words text-lg">{request.title}</CardTitle>
              <Badge variant={statusVariants[request.status]}>{request.status}</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {request.requester} · {new Date(request.createdAt).toLocaleDateString()}
            </p>
          </CardHeader>
          <CardContent className="grid gap-3">
            <p className="font-semibold tabular-nums">{request.formattedAmount}</p>
            <p className="whitespace-pre-wrap break-words text-sm">{request.justification}</p>
            {request.reviewer && (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p className="font-medium">Reviewed by {request.reviewer}</p>
                {request.feedback && <p className="mt-1 whitespace-pre-wrap break-words">{request.feedback}</p>}
              </div>
            )}
            {actions(request)}
          </CardContent>
        </Card>
      ))}
      {(collection.previous || collection.next) && (
        <nav aria-label="Budget request pages" className="flex items-center gap-3">
          {collection.previous && (
            <Button asChild variant="outline" size="sm">
              <Link href={pageHref(collection.previous)} preserveScroll>Previous</Link>
            </Button>
          )}
          <span className="text-sm">Page {collection.page}</span>
          {collection.next && (
            <Button asChild variant="outline" size="sm">
              <Link href={pageHref(collection.next)} preserveScroll>Next</Link>
            </Button>
          )}
        </nav>
      )}
    </div>
  )
}
