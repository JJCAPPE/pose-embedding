import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { supabaseEnvironment } from "@/lib/env";

export async function createSupabaseServerClient() {
  const environment = supabaseEnvironment();
  if (!environment) return null;

  const cookieStore = await cookies();
  return createServerClient(environment.url, environment.publishableKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const cookie of cookiesToSet) {
            cookieStore.set(cookie.name, cookie.value, cookie.options);
          }
        } catch {
          // Server Components cannot set cookies. The proxy refreshes sessions.
        }
      },
    },
  });
}
