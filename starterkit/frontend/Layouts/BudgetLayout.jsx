import { Link, router, usePage } from "@inertiajs/react"
import { Button } from "@/Components/ui/button"
import { FlashMessages } from "@/Components/admin/FlashMessages"
import { useRoute } from "@/composables/useRoute"

export function BudgetLayout({ children }) {
  const route = useRoute()
  const { auth, flash } = usePage().props

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3">
          <Link href={route("budget_index")} className="font-semibold">Project budgets</Link>
          {auth?.user && (
            <div className="flex items-center gap-3">
              <span className="hidden text-sm text-muted-foreground sm:inline">{auth.user.username}</span>
              <Button variant="outline" size="sm" onClick={() => router.post(route("logout"), { budget: true })}>
                Sign out
              </Button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto grid max-w-5xl gap-6 px-4 py-8">
        <FlashMessages messages={flash} />
        {children}
      </main>
    </div>
  )
}
