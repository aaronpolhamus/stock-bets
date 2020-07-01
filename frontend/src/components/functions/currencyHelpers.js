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

export { simplifyCurrency }
