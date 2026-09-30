# Shared header and footer

Edit `components/header.html` or `components/footer.html`, then run from the project root:

```sh
python3 scripts/build.py
```

The build updates all marked HTML pages. Publish the generated pages along with `assets/`. Header styles remain in the existing theme CSS; footer styles live in `assets/css/footer.css`.

To add a page, reuse the existing page head, styles and script imports. Inside the page wrapper, insert:

```html
<!-- shared:header:start -->
<!-- shared:header:end -->

<main>Your page content</main>

<!-- shared:footer:start -->
<!-- shared:footer:end -->
```

Run the build to populate both includes. Nested pages automatically receive the correct relative paths for component images and the footer stylesheet. Adjust the page's other CSS/script paths for its location. Search, sidebar and mobile navigation markup are all owned by the shared header. Existing theme scripts must load after the header.

The current site is a static presentation with placeholder links; component extraction preserves that behavior.
