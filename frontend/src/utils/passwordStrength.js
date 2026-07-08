// frontend/src/utils/passwordStrength.js
//
// Client-side mirror of backend/app/core/password_policy.py. Purely a UX aid
// so the user sees requirements green up as they type. The backend enforces
// the same rules and rejects on submit — never trust the frontend alone.

const MIN_LEN = 10;
const MAX_LEN = 128;

// Keep in sync with _BAD_PASSWORDS on the backend. Small on purpose.
const BAD_PASSWORDS = new Set([
  "password", "password1", "password123", "passw0rd",
  "12345678", "123456789", "1234567890", "1234567",
  "qwerty", "qwerty123", "qwertyui", "qwertyuiop",
  "abcdef", "abc12345", "abcdefgh",
  "letmein", "welcome", "welcome1", "welcome123",
  "admin", "administrator", "admin123", "root", "root123",
  "iloveyou", "monkey", "dragon", "master",
  "1qaz2wsx", "zaq12wsx",
  "kenya", "nairobi", "mombasa", "safaricom",
]);

const emailLocalPart = (email) => {
  if (!email) return null;
  const local = email.split("@")[0].trim().toLowerCase();
  return local || null;
};

/**
 * Evaluate a password against the MVP policy.
 * Returns:
 *   {
 *     score: 0-5,          // rough visual gauge (bar width)
 *     checks: { length, classes, notCommon, notEmail, notTooLong },
 *     allPassed: boolean,  // true when the password can be submitted
 *   }
 */
export function checkPasswordStrength(password = "", email = "") {
  const pw = password || "";
  const lowered = pw.toLowerCase();

  const hasUpper = /[A-Z]/.test(pw);
  const hasLower = /[a-z]/.test(pw);
  const hasDigit = /\d/.test(pw);
  const hasSymbol = /[^A-Za-z0-9]/.test(pw);
  const classCount = [hasUpper, hasLower, hasDigit, hasSymbol].filter(Boolean).length;

  const local = emailLocalPart(email);
  const containsEmail = !!(local && local.length >= 3 && lowered.includes(local));

  const checks = {
    length: pw.length >= MIN_LEN,
    notTooLong: pw.length <= MAX_LEN,
    classes: classCount >= 3,
    notCommon: !BAD_PASSWORDS.has(lowered),
    notEmail: !containsEmail,
  };

  const allPassed = Object.values(checks).every(Boolean);

  // Rough gauge — 1 point per check plus a bonus point for a very long pw.
  let score = 0;
  if (checks.length) score++;
  if (checks.classes) score++;
  if (checks.notCommon) score++;
  if (checks.notEmail) score++;
  if (pw.length >= 14) score++;

  return { score, checks, allPassed };
}
