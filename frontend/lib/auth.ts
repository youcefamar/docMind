import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "DocMind Admin Credentials",
      credentials: {
        username: { label: "Username or Email", type: "text", placeholder: "admin@docmind.internal" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // Simple demo credentials verification (Admin pass: docmind2026 or admin)
        if (
          (credentials?.username === "admin@docmind.internal" || credentials?.username === "admin") &&
          (credentials?.password === "docmind2026" || credentials?.password === "admin")
        ) {
          return {
            id: "usr_1001",
            name: "DocMind Admin",
            email: "admin@docmind.internal",
            role: "administrator"
          };
        }
        
        // Allow general employee guest login for demo
        if (credentials?.username && credentials?.password) {
          return {
            id: "usr_" + Math.floor(Math.random() * 1000),
            name: credentials.username.split("@")[0],
            email: credentials.username,
            role: "employee"
          };
        }

        return null;
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id = token.sub;
        (session.user as any).role = token.role || "employee";
      }
      return session;
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as any).role;
      }
      return token;
    }
  },
  secret: process.env.NEXTAUTH_SECRET || "docmind-super-secret-key-2026",
};
