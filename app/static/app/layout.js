document.addEventListener("DOMContentLoaded", () => {
  const header = document.getElementById("siteHeader");
  const burger = document.getElementById("navBurger");
  const mobileMenu = document.getElementById("mobileMenu");
  const sentinel = document.getElementById("heroSentinel");

  if (burger && mobileMenu) {
    burger.addEventListener("click", () => mobileMenu.classList.toggle("is-open"));
  }

  if (!header) return;

  const setMode = (mode) => {
    header.classList.remove("is-hero", "is-solid");
    header.classList.add(mode);
  };

  setMode("is-hero");

  if (sentinel && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      ([entry]) => {
        setMode(entry.isIntersecting ? "is-hero" : "is-solid");
      },
      {
        threshold: 0,
        rootMargin: "-74px 0px 0px 0px" 
      }
    );
    io.observe(sentinel);
  } else {
    const onScroll = () => setMode(window.scrollY < 10 ? "is-hero" : "is-solid");
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }
});
