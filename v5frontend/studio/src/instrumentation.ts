export async function register() {
  if (typeof (globalThis as any).self === 'undefined') {
    (globalThis as any).self = globalThis;
  }
}
