/**
 * NEXT_PUBLIC_* variables are substituted into the client bundle at BUILD
 * time, not read at runtime. Setting NEXT_PUBLIC_API_BASE_URL as a runtime-
 * only variable on the host silently ships the localhost fallback to every
 * visitor: their browser probes port 8000 on their own machine, the
 * connection is refused, and the page reports the API unreachable while the
 * backend is perfectly healthy.
 *
 * That failure is invisible until someone opens the public link, so the
 * production build refuses to proceed without it.
 */
if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_BASE_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_BASE_URL must be set at BUILD time for a production " +
      "build. Setting it as a runtime-only variable has no effect — the " +
      "value is inlined into the bundle during `next build`.",
  );
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output keeps the container image small for the Render deploy.
  output: "standalone",
};

export default nextConfig;
