# FV-110 — Responsive Design and Browser Compatibility Testing

## Objective
Verify the Boston Events application across desktop, tablet, and mobile screen sizes.

## Desktop Browser Testing

| Browser | 360 px | 390 px | 768 px | 1280 px |
|---|---|---|---|---|
| Chrome | Pass | Pass | Pass | Pass |
| Firefox | Pass | Pass | Pass | Pass |
| Safari | Pass | Pass | Pass | Pass |

These tests used desktop browsers at different viewport widths.

## Physical iPhone Testing

Browser: Safari
Result: All five checks passed.

- Navigation and event cards display correctly.
- Login and registration forms work.
- Chat input and buttons work.
- Mobile keyboard does not obscure required controls.
- No horizontal scrolling, clipping, or overlapping elements.

## Responsive CSS Changes

Updated code/Web_Application/src/styles.css to improve:
- Mobile navigation and dashboard spacing.
- Event card layout and text wrapping.
- Chat panel scrolling and button sizing.
- Touch-friendly form controls.
- Login dialog sizing on narrow screens.

## Production Build

Command: npm run build
Vite version: 6.4.4
Result: Pass (34 modules transformed).

## Not Tested

- Microsoft Edge desktop
- Chrome on Android

## Remaining Documentation

- Record exact desktop browser versions.
- Record iPhone model and iOS version.
- Retest after subsequent interface changes.

## Conclusion

All reported manual tests passed. The application was tested at
four viewport widths in three desktop browsers and on a physical iPhone.
