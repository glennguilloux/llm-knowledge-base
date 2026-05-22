---
id: "typescript-web-nextauth-setup"
title: "NextAuth.js Setup with Providers and Callbacks"
language: "typescript"
category: "web"
subcategory: "auth"
tags: ["nextauth", "auth", "oauth", "credentials", "session", "jwt", "providers"]
version: "5.0+"
retrieval_hint: "NextAuth.js Auth.js setup providers credentials session JWT callbacks"
last_verified: "2026-05-22"
confidence: "high"
---

# NextAuth.js Setup with Providers and Callbacks

## When to Use
- Authentication in Next.js applications (App Router or Pages Router)
- Social login (Google, GitHub, Discord)
- Email/password (credentials) authentication
- Session management with JWT or database sessions

## Standard Pattern

```typescript
// --- app/api/auth/[...nextauth]/route.ts (App Router) ---
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GitHubProvider from "next-auth/providers/github";
import bcrypt from "bcryptjs";

const handler = NextAuth({
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const user = await db.user.findUnique({ where: { email: credentials.email } });
        if (!user) return null;

        const isValid = await bcrypt.compare(credentials.password, user.passwordHash);
        if (!isValid) return null;

        return { id: String(user.id), email: user.email, name: user.name };
      },
    }),
  ],

  session: { strategy: "jwt", maxAge: 30 * 24 * 60 * 60 },  // 30 days

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as any).role ?? "user";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    },
    async redirect({ baseUrl }) {
      return baseUrl + "/dashboard";
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },
});

export { handler as GET, handler as POST };

// --- types/next-auth.d.ts (extend session types) ---
// declare module "next-auth" {
//   interface Session {
//     user: { id: string; role: string } & DefaultSession["user"];
//   }
// }
// declare module "next-auth/jwt" {
//   interface JWT { id: string; role: string }
// }

// --- Client-side usage ---
"use client";
import { useSession, signIn, signOut } from "next-auth/react";

function AuthButton() {
  const { data: session, status } = useSession();

  if (status === "loading") return <span>Loading...</span>;
  if (!session) return <button onClick={() => signIn()}>Sign in</button>;
  return (
    <div>
      <span>{session.user.email}</span>
      <button onClick={() => signOut()}>Sign out</button>
    </div>
  );
}

// --- Server-side usage (App Router) ---
import { getServerSession } from "next-auth";

async function DashboardPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");

  return <div>Welcome, {session.user.name}</div>;
}
```

## Common Mistakes

```typescript
// WRONG: Missing NEXTAUTH_SECRET
// .env.local: No NEXTAUTH_SECRET defined
// Session cookies won't be encrypted!

// CORRECT: Always set NEXTAUTH_SECRET in .env.local
// NEXTAUTH_SECRET=your-random-secret-here

// WRONG: Not extending session types
session.user.id  // TypeScript error: Property 'id' does not exist

// CORRECT: Extend types in next-auth.d.ts
// See types/next-auth.d.ts above

// WRONG: Using authorize() without proper validation
async authorize(credentials) {
  return { id: "1", email: credentials.email };  // No password check!

// CORRECT: Validate credentials against database
async authorize(credentials) {
  const user = await db.user.findUnique({ where: { email: credentials.email } });
  if (!user || !await bcrypt.compare(credentials.password, user.password)) return null;
  return { id: String(user.id), email: user.email };
}

// WRONG: Accessing session in API route without getServerSession
const session = await getSession({ req });  // Deprecated API

// CORRECT: Use getServerSession
const session = await getServerSession(authOptions);
```

## Gotchas
- `NEXTAUTH_SECRET` is required for production — generate with `openssl rand -base64 32`
- `NEXTAUTH_URL` is auto-detected in production but must be set in development
- Credentials provider doesn't support JWT rotation by default — use database sessions for security
- `session` callback receives the JWT token; `jwt` callback fires on sign-in and token refresh
- `pages.signIn` overrides the default sign-in page
- Server components use `getServerSession()`; client components use `useSession()`
- Wrap your app in `<SessionProvider>` for client-side session access
- OAuth providers need callback URLs configured in their developer consoles

## Related
- typescript/web/nextjs/app-router.md
- typescript/web/express/middleware.md
- security/authentication.md
