export function supabaseEnvironment() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  return url && publishableKey ? { url, publishableKey } : null;
}

export function editingIsEnabled(): boolean {
  return process.env.EDITING_ENABLED === "true" && supabaseEnvironment() !== null;
}
