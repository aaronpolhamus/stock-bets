import React from 'react'
import styled from 'styled-components'
import { Table, Badge } from 'react-bootstrap'
import { SectionTitle } from 'components/textComponents/Text'
import { UserMiniCard } from 'components/users/UserMiniCard'

const StyledBadge = styled(Badge)`
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-smallcaps);
`

const setPillVariant = (status) => {
  switch (status) {
    case 'joined':
      return 'success'
    case 'invited':
      return 'info'
    case 'declined':
      return 'danger'
    default:
      return 'info'
  }
}

const PendingGameParticipants = ({ participants }) => {
  const participantsBuilder = (participants) => {
    return participants.map((participant, index) => {
      return (
        <tr>
          <td key={index}>
            <UserMiniCard
              avatarSrc={participant.profile_pic}
              avatarSize='small'
              username={participant.username}
            />
          </td>
          <td>
            <StyledBadge pill variant={setPillVariant(participant.status)}>
              {participant.status}
            </StyledBadge>
          </td>
        </tr>
      )
    })
  }

  return (
    <div>
      <SectionTitle>Participants</SectionTitle>
      <Table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{participants && participantsBuilder(participants)}</tbody>
      </Table>
    </div>
  )
}

export { PendingGameParticipants }
