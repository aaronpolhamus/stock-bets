import React from 'react'
import styled from 'styled-components'
import { Table, Badge } from 'react-bootstrap'
import { SectionTitle } from 'components/textComponents/Text'
import { PlayerRow } from 'components/lists/PlayerRow'
import PropTypes from 'prop-types'
import { Send } from 'react-feather'

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

const PendingGameParticipants = ({ participants, invitees }) => {
  const participantsBuilder = (participants) => {
    return participants.map((participant, index) => {
      return (
        <tr key={index}>
          <td>
            <PlayerRow
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

  const inviteesBuilder = (invitees) => {
    return invitees.map((invitee, index) => {
      return (
        <tr key={index}>
          <td>
            <p
              style={{
                fontSize: 'var(--font-size-normal)',
                color: 'var(--color-text-gray)'
              }}
            >
              <Send
                size={18}
                style={{
                  marginRight: '10px',
                  marginLeft: 'var(--space-50)'
                }}
              />

              {invitee}
            </p>
          </td>
          <td>
            <StyledBadge pill variant='info'>
              Invited by mail
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
        <tbody>
          {participants && participantsBuilder(participants)}
          {participants && inviteesBuilder(invitees)}
        </tbody>
      </Table>
    </div>
  )
}

PendingGameParticipants.propTypes = {
  participants: PropTypes.array,
  invitees: PropTypes.array
}

export { PendingGameParticipants }
