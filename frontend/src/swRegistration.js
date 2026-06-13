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
    const registrations = await navigator.serviceWorker.getRegistrations();
    for (const item of registrations) {
      const scriptUrl = item.active?.scriptURL || item.waiting?.scriptURL || item.installing?.scriptURL || '';
      const isExpected = scriptUrl.includes('/sw.js');
      const isRootScope = item.scope.endsWith('/');
      if (!isExpected || !isRootScope) {
        await item.unregister();
      }
    }

    const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    await registration.update();

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

    setInterval(() => {
      registration.update().catch(() => {});
    }, 60 * 60 * 1000);
  } catch (error) {
    console.error('Service worker registration failed:', error);
  }
}
