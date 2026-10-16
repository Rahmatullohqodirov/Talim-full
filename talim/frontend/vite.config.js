import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      // Ilova ochilganda offline holatda ham ishlashi uchun (app shell + oxirgi ko'rilgan ma'lumotlar keshlanadi)
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico}"],
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            // Darslar/hikoyalar — bir marta ko'rilgan bo'lsa, offline holatda ham ochiladi
            // (avval keshdan darhol ko'rsatadi, fonda internet bo'lsa yangilaydi — ro'yxat va bitta dars/hikoya tafsiloti)
            urlPattern: ({ url, request }) =>
              request.method === "GET" &&
              (url.pathname.startsWith("/api/v1/lessons") || url.pathname.startsWith("/api/v1/stories")),
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "talim-lessons-offline-cache",
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Qolgan GET so'rovlar (ro'yxatlar) — avval tarmoqdan urinadi, ishlamasa keshdan ko'rsatadi
            urlPattern: ({ url, request }) =>
              request.method === "GET" && url.pathname.startsWith("/api/v1/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "supertutor-api-cache",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      manifest: {
        name: "Talim",
        short_name: "Talim",
        description: "AI asosidagi til va matematika o'qitish platformasi",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#6d5ce8",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      devOptions: {
        enabled: true,
      },
    }),
  ],
});
