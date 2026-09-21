/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output keeps the container image small for the Render deploy.
  output: "standalone",
};

export default nextConfig;
