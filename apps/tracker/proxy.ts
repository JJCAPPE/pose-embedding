import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";
import { supabaseEnvironment } from "@/lib/env";

export async function proxy(request: NextRequest) {
  const environment = supabaseEnvironment();
  if (!environment) return NextResponse.next({ request });

  let response = NextResponse.next({ request });
  const supabase = createServerClient(environment.url, environment.publishableKey, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(cookiesToSet) {
        for (const cookie of cookiesToSet) {
          request.cookies.set(cookie.name, cookie.value);
        }
        response = NextResponse.next({ request });
        for (const cookie of cookiesToSet) {
          response.cookies.set(cookie.name, cookie.value, cookie.options);
        }
      },
    },
  });

  await supabase.auth.getClaims();
  return response;
}

export const config = {
  matcher: ["/edit/:path*", "/login"],
};
