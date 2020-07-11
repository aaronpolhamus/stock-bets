const breakpointKeys = [
  'xs',
  'sm',
  'md',
  'lg',
  'xl'
]

// We are getting all the values from the bootstrap's breakpoint custom properties
const breakpoints = breakpointKeys.reduce((acc, key) => {
  // transform body computed styles to a constant for legibility
  const bodyStyles = window.getComputedStyle(document.body)

  // this gets a single breakpoint value
  const breakpointValue = bodyStyles.getPropertyValue(`--breakpoint-${key}`)

  // We add the key-value pair to the final object and destructure the previous accumulated pairs to get all of them in the end
  return { ...acc, [key]: breakpointValue.trim() }
}, {})

export { breakpoints }
