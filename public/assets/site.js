const carousel = document.querySelector("[data-carousel]");
if (carousel) {
  const slides = Array.from(carousel.querySelectorAll("[data-slide]"));
  const track = carousel.querySelector("[data-carousel-track]");
  const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
  const previous = carousel.querySelector("[data-carousel-prev]");
  const next = carousel.querySelector("[data-carousel-next]");
  let index = 0;

  const moveTrack = () => {
    if (!track) return;
    const slideWidth = slides[0]?.getBoundingClientRect().width || carousel.clientWidth;
    const gap = Number.parseFloat(getComputedStyle(track).columnGap || "0");
    track.style.transform = `translateX(${-index * (slideWidth + gap)}px)`;
  };

  const show = (nextIndex) => {
    slides[index]?.classList.remove("is-active");
    dots[index]?.classList.remove("is-active");
    dots[index]?.setAttribute("aria-current", "false");
    index = (nextIndex + slides.length) % slides.length;
    slides[index]?.classList.add("is-active");
    dots[index]?.classList.add("is-active");
    dots[index]?.setAttribute("aria-current", "true");
    moveTrack();
  };

  let timer = window.setInterval(() => show(index + 1), 6000);
  const restart = () => {
    window.clearInterval(timer);
    timer = window.setInterval(() => show(index + 1), 6000);
  };

  previous?.addEventListener("click", () => {
    show(index - 1);
    restart();
  });

  next?.addEventListener("click", () => {
    show(index + 1);
    restart();
  });

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      show(Number(dot.dataset.carouselDot || 0));
      restart();
    });
  });

  window.addEventListener("resize", moveTrack);
  moveTrack();
}
