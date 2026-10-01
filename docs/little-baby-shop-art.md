# Little Baby Shop — art direction

## Audit and choice
The old arches, uniform inline SVG icons, CSS clouds/hills, bird scenes, picnic tape, block stages and book-spine brand cards made the product photographs feel disconnected. They have been removed. Of three directions (illustrated nursery, wooden playground, product-photography select shop), the tactile select shop best supports real shopping photography and precise comparison.

One world: shop overview → departments → product shelves → paper price tags → recommended shelf → brand shelf → shopping tray → price-tag history. No decorative character, stars, clouds or continuous floating motion.

## Three primary views
- Hero: one original shop scene, with live HTML heading and four accessible department links on paper labels. Desktop and mobile use separately composed images; no important category is cropped away. Objects in the scene are illustrative, unbranded and do not represent specific listings or prices.
- Products: actual listing photo beside the prominent unit-price tag. Cloth-style strength labels, secondary total price/quantity, precise history, disclosure for calculations. The shelf edge uses a strip of the actual wood image.
- Comparison: three photo slots in a small wooden tray; selection, remaining capacity, removal and a 2–3 product modal preserve existing data and analytics hooks. Removal touch areas are 44px. Existing keyboard focus, inert background and session restoration remain.

## Palette and typography
Ivory #faf8f2, milk #fffefa, sage #e4e9df, deep blue-green #294e50. Real wood contributes warm neutral color; category colors are restricted to small identifiers. Native Japanese Mincho for editorial headings, Georgia for numerical price tags, system sans-serif for reading. No remote font dependency.

## Original art: built-in image generation
The artwork was generated using the built-in image-generation tool. WebP conversion is compression only. The source compositions are 1536×1024 (wide) and 1024×1536 (mobile), delivered as `src/static/shop-wide.webp` and `src/static/shop-mobile.webp`.

### Wide composition prompt specification
Create a premium editorial product-photography key visual for an original miniature baby select shop. Natural pale ash wood, ivory plaster, cream cotton muslin, tactile textiles, restrained sage shelving, soft daylight from the left. Leave generous quiet ivory wall at upper left for live Japanese headline. Four distinct unbranded product arrangements across one wooden display: diapers in a birch box; ivory wipes with a sage lid; butter-lid formula tin and a realistic baby bottle; folded pale lavender disposal bags and a small sage waste bin. Blank paper price tags, subtle realistic material detail, balanced commercial lookbook composition. No text, logos, mascots, stars, clouds, flat icons, geometric illustrations, arch category cards or excessive decorations. Objects must feel physically plausible and harmonious with real product photography.

### Mobile companion prompt specification
Recompose the same original shop and material language into a portrait 2:3 frame. Keep the upper approximately 38% quiet ivory wall for live headline. Arrange diapers left and wipes right on the upper shelf (approximately 45–58% vertical position), formula and bottle left and folded disposal bags with the waste bin right on the lower shelf (approximately 70–88%). Blank paper labels near the front of each shelf, minimal edge foliage, realistic cotton and wood grain. Preserve lighting, product identity, restraint and tactile quality. No text, logos, characters or new decorative motifs.

## Preservation and checks
Only presentation rendering, stylesheet and visual assertions change. Product fetching, parsing, quality exclusion, quantity/unit calculations, duplicates, history snapshots, affiliate links, GA4 hooks, SEO generation rules and deployment workflow remain. Price graphs remain data-driven SVG; decorative SVG artwork is removed. Reduced-motion preferences remain respected.

QA: Python regression suite, real-browser widths 320/390/768/1440, photo containment, three-slot limit, 2/3-column modal, keyboard focus/inert background, session restoration, brand reset, sorting, condition selection and GA4 event dispatch. Deployment and live-page checks are reported separately after publishing.
