import React from 'react'
import api from 'services/api'
import { LogOut as LogoutIcon } from 'react-feather'
import { AuxiliarButton } from 'components/ui/buttons/AuxiliarButton'

const LogoutButton = () => {
  const handleLogout = async () => {
    await api.post('/api/logout')
    window.location.assign('/')
  }
  return (
    <AuxiliarButton variant='link' onClick={handleLogout}>
      <LogoutIcon />
      <span> Logout</span>
    </AuxiliarButton>
  )
}

export { LogoutButton }
