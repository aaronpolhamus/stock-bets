import React, { useEffect, useState } from 'react'
import { apiPost } from 'components/functions/api'
import { PlayerRow } from 'components/lists/PlayerRow'
import { SmallCaps } from 'components/textComponents/Text'
import styled from 'styled-components'
import { formatPercentage } from 'components/functions/formattingHelpers'

const ListRankingWrapper = styled.ol`
  font-size: var(--font-size-small);
  padding-inline-start: 30px;
`

const ListRankingItem = styled.li`
  padding: var(--space-100) 0;
  color: var(--color-text-light-gray);
  margin-bottom: var(--space-50);
  cursor: pointer;
`

const ListHeader = styled.div`
  display: flex;
  font-size: --font-size-small;
  justify-content: space-between;
  margin-bottom: var(--space-200);
  color: var(--color-text-light-gray);
  padding-bottom: var(--space-100);
`
const NumberHeading = styled.span`
  display: inline-block;
  width: 23px;
  margin-right: var(--space-100);
  text-align: right;
`

const GlobalLeaderboard = () => {
  const [listRanking, setListRanking] = useState({})
  const [listFriends, setListFriends] = useState({})

  const getListRanking = async () => {
    await apiPost('public_leaderboard')
      .then((response) => {
        setListRanking(response)
      })
  }

  // This api call could be made outside of the component because it's shared with tht friends list, I just made it here to avoid mixing patterns but we need to eventually refactor this two comps to make it one.
  const getListFriends = async () => {
    await apiPost('get_list_of_friends')
      .then((response) => {
        setListFriends(response)
      })
  }

  useEffect(() => {
    getListRanking()
    getListFriends()
  }, [])

  console.log(listRanking, listFriends)
  const listBuilder = (data) => {
    return data.map((friend, index) => {
      const isFriend = listFriends.length > 0 && listFriends.findIndex((row) => {
        return row.id === friend.user_id
      })
      const isMarketIndex = friend.user_id === null
      console.log(isFriend, isMarketIndex)

      return (
        <ListRankingItem key={index}>
          <PlayerRow
            avatarSrc={friend.profile_pic}
            avatarSize='24px'
            username={friend.username}
            isMarketIndex={isMarketIndex}
            isFriend={isFriend !== -1}
            isCurrentPlayer={''}
            nameFontSize='var(--font-size-small)'
            nameColor='var(--color-light-gray)'
            info={[friend.rating, formatPercentage(friend.total_return, 2)]}
          />
        </ListRankingItem>
      )
    })
  }

  return (
    <>
      <ListHeader>
        <SmallCaps><NumberHeading>N. </NumberHeading>Player</SmallCaps>
        <SmallCaps>Rating <span style={{ color: 'var(--color-primary-darken)', fontWeight: 'bold' }}>|</span> Avg. Return</SmallCaps>
      </ListHeader>
      <ListRankingWrapper>
        {listRanking.length > 0 && listBuilder(listRanking)}
      </ListRankingWrapper>
    </>
  )
}

export { GlobalLeaderboard }