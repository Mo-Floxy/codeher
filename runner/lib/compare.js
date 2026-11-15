/**
 * Structural equality for values that crossed a vm context boundary.
 *
 * The actual value was built inside the sandbox realm, so its prototypes are not
 * the ones this module can see: every check below has to be realm-agnostic
 * (Array.isArray, Object.prototype.toString, constructor names) rather than
 * `instanceof` or a direct prototype comparison. Booleans and numbers are kept
 * strictly apart so a solution returning `true` cannot pass an expectation of `1`.
 */

function sameType(a, b) {
  if (typeof a !== typeof b) return false;
  if (a === null || b === null) return a === b;
  const aIsArray = Array.isArray(a);
  const bIsArray = Array.isArray(b);
  if (aIsArray || bIsArray) return aIsArray && bIsArray;
  if (typeof a === "object") return isPlainObject(a) && isPlainObject(b);
  return true;
}

function isPlainObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const proto = Object.getPrototypeOf(value);
  return proto === null || proto.constructor?.name === "Object";
}

function deepEqual(a, b) {
  if (Object.is(a, b)) return true;
  if (typeof a === "number" && typeof b === "number") return a === b;
  if (!sameType(a, b)) return false;
  if (a === null || typeof a !== "object") return false;

  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    return a.every((item, index) => deepEqual(item, b[index]));
  }

  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;
  return aKeys.every((key) => Object.hasOwn(b, key) && deepEqual(a[key], b[key]));
}

/** JSON-safe rendering of an actual value for the test feedback panel. */
function toDisplay(value, depth = 0) {
  if (depth > 4) return "…";
  if (value === undefined) return null;
  if (value === null || typeof value === "boolean") return value;
  if (typeof value === "number") return Number.isFinite(value) ? value : String(value);
  if (typeof value === "string") return value.length > 200 ? `${value.slice(0, 200)}…` : value;
  if (typeof value === "function") return `[Function ${value.name || "anonymous"}]`;
  if (Array.isArray(value)) return value.slice(0, 50).map((item) => toDisplay(item, depth + 1));
  if (value instanceof Set) return [...value].slice(0, 50).map((item) => toDisplay(item, depth + 1));
  if (value instanceof Map) {
    return Object.fromEntries([...value].slice(0, 50).map(([k, v]) => [String(k), toDisplay(v, depth + 1)]));
  }
  if (typeof value === "object") {
    if (isPlainObject(value)) {
      return Object.fromEntries(Object.keys(value).slice(0, 30).map((k) => [k, toDisplay(value[k], depth + 1)]));
    }
    return String(value);
  }
  return String(value);
}

module.exports = { deepEqual, toDisplay, isPlainObject };
