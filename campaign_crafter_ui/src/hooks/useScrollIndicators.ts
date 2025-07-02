import { useState, useEffect, RefObject, useCallback } from 'react';

interface ScrollIndicatorState {
  showLeftIndicator: boolean;
  showRightIndicator: boolean;
}

function useScrollIndicators(scrollRef: RefObject<HTMLElement>): ScrollIndicatorState {
  const [scrollState, setScrollState] = useState<ScrollIndicatorState>({
    showLeftIndicator: false,
    showRightIndicator: false,
  });

  const checkScrollPosition = useCallback(() => {
    const element = scrollRef.current;
    if (element) {
      const currentScrollLeft = Math.round(element.scrollLeft); // Round to avoid floating point issues
      const maxScrollLeft = Math.round(element.scrollWidth - element.clientWidth);

      // Add a small tolerance for floating point comparisons
      const tolerance = 1;

      const canScrollLeft = currentScrollLeft > tolerance;
      const canScrollRight = currentScrollLeft < (maxScrollLeft - tolerance);

      // console.log(`SL: ${currentScrollLeft}, MaxSL: ${maxScrollLeft}, SW: ${element.scrollWidth}, CW: ${element.clientWidth}`);


      setScrollState({
        showLeftIndicator: canScrollLeft,
        showRightIndicator: canScrollRight && maxScrollLeft > 0, // Also ensure there is actually something to scroll
      });
    }
  }, [scrollRef]);

  useEffect(() => {
    const element = scrollRef.current;
    if (element) {
      // Initial check
      checkScrollPosition();

      element.addEventListener('scroll', checkScrollPosition);
      // Also check on resize, as clientWidth might change
      window.addEventListener('resize', checkScrollPosition);

      // MutationObserver to detect changes in content (e.g., items added/removed)
      // which might affect scrollWidth
      const observer = new MutationObserver(checkScrollPosition);
      observer.observe(element, { childList: true, subtree: true });


      return () => {
        element.removeEventListener('scroll', checkScrollPosition);
        window.removeEventListener('resize', checkScrollPosition);
        observer.disconnect();
      };
    }
  }, [scrollRef, checkScrollPosition]);

  return scrollState;
}

export default useScrollIndicators;
