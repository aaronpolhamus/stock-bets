import moment from 'moment-timezone'

const simplifyCurrency = (value, decimals, dollarSign) => {
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

  decimals = decimals === undefined ? 1 : decimals

  amount = amount / baseline
  amount = decimals ? amount.toFixed(decimals) : amount
  amount = dollarSign ? `$${amount}${affix}` : `${amount}${affix}`

  return amount
}

const formatPercentage = (value, fixedPoints) => {
  const normalizedValue = parseFloat(value).toFixed(fixedPoints || 3)
  return `${normalizedValue}%`
}

const toCurrency = (value) => {
  return `$${value.toLocaleString(undefined,
 { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const toFormattedDate = (value, format) => {
  format = format || 'MMM D, HH:mm'
  return `${moment(value * 1000).tz('America/New_York').format(format)} EST`
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

const daysLeft = endTimePosix => {
  const endMilliseconds = endTimePosix * 1000
  const today = new Date().getTime()

  const timeleft = endMilliseconds - today

  const days = msToDays(timeleft)

  if (days < 0) return 'Game ended'

  switch (days) {
    case 0:
      return `Ends today at ${toFormattedDate(endTimePosix)}`
    case 1:
      return `Ends tomorrow at ${toFormattedDate(endTimePosix)}`
    default:
      return `${days} days left`
  }
}

export { simplifyCurrency, numberToOrdinal, msToDays, daysLeft, toCurrency, toFormattedDate, formatPercentage }
