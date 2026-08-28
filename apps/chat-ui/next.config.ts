import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The chat UI talks to a local FastAPI server. Allow it in dev.
  async rewrites() {
    return [
      {
        source: "/v1/:path*",
        destination: `${process.env.NEXT_PUBLIC_AGENT_BASE_URL ?? "http://localhost:8000"}/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
