export async function registerServiceWorker() {
  if (typeof window === 'undefined') {
    return;
  }

  if (!('serviceWorker' in navigator)) {
    return;
  }

  if (!window.isSecureContext) {
    return;
  }

  // Keep service worker only in production so local development stays predictable.
  const isProduction = import.meta.env.PROD;
  if (!isProduction) {
    try {
      const existing = await navigator.serviceWorker.getRegistration('/');
      if (existing) {
        await existing.unregister();
      }
    } catch (error) {
      console.warn('Service worker cleanup failed in development:', error);
    }
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });

    registration.addEventListener('updatefound', () => {
      const worker = registration.installing;
      if (!worker) {
        return;
      }
      worker.addEventListener('statechange', () => {
        if (worker.state === 'installed' && navigator.serviceWorker.controller) {
          // The updated worker takes control immediately via skipWaiting/clients.claim.
          console.info('Service worker updated.');
        }
      });
    });
  } catch (error) {
    console.error('Service worker registration failed:', error);
  }
}
