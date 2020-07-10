const filterEntries = (array, filters) => {
  const filtered = array.filter((entry, index) => {
    return Object.keys(filters).every((key, value) => {
      return entry[key] === filters[key]
    })
  })
  return filtered
}

export { filterEntries }
