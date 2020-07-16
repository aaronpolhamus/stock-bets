const simplifyCurrency = (value) => {
  let affix = ''
  let baseline = 1
  let amount = value

  if (amount >= 1000000000) {
    baseline = 1000000000
    affix = 'B'
  } else if (amount >= 1000000) {
    baseline = 1000000
    affix = 'M'
  } else if (amount >= 1000) {
    baseline = 1000
    affix = 'K'
  }

  amount = amount / baseline
  amount = amount.toFixed(1)
  amount = `$${amount}${affix}`

  return amount
}

const numberToOrdinal = number => {
  const suffixes = ['th', 'st', 'nd', 'rd']
  const suffixIndex = number % 100
  const suffix = suffixes[(suffixIndex - 20) % 10] ||
    suffixes[suffixIndex] || suffixes[0]

  return `${number}${suffix}`
}

const msToDays = milliseconds => {
  return Math.floor(milliseconds / 86400000)
}

const daysLeft = milliseconds => {
  const days = msToDays(milliseconds)
  if (days <= 0) {
    return 'Ends today'
  } else {
    return `${days} days left`
  }
}

export { simplifyCurrency, numberToOrdinal, msToDays, daysLeft }
