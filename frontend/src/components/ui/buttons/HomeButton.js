import React, { useState } from 'react'
import { ChevronLeft } from 'react-feather'
import { AuxiliarButton } from 'components/ui/buttons/AuxiliarButton'
import { Redirect } from 'react-router-dom'

const HomeButton = () => {
  const [redirect, setRedirect] = useState(false)

  if (redirect) return <Redirect to='/' />

  return (
    <AuxiliarButton
      variant='link' onClick={() => {
        setRedirect(true)
      }}
    >
      <ChevronLeft />
      <span> Home</span>
    </AuxiliarButton>
  )
}

export { HomeButton }
