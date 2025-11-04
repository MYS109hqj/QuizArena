

export const debounce = function debounceWithImmediateCheck(func, wait, immediate=false) {

  let timeout = null;
  return (...args) => {
    const context = this;
    if (immediate && !timeout) func.apply(context, args);
    clearTimeout(timeout);
    timeout = setTimeout(() => { if (!immediate) func.apply(context, args); timeout = null; }, wait);
  };
}

