import React, { useEffect, useState } from 'react'
import { apiPost } from 'components/functions/api'
import { UserMiniCard } from 'components/users/UserMiniCard'
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
`

const ListHeader = styled.div`
  display: flex;
  font-size: --font-size-small;
  justify-content: space-between;
  margin-bottom: var(--space-200);
  color: var(--color-text-light-gray);
  padding-bottom: var(--space-100);
  span {
    display: inline-block;
    width: 23px;
    margin-right: var(--space-100);
    text-align: right;
  }
`

const ListGlobalRanking = () => {
  const [listRanking, setListRanking] = useState({})

  const getListRanking = async () => {
    const list = await apiPost('public_leaderboard')
    setListRanking(list)
  }

  useEffect(() => {
    getListRanking()
  }, [])

  const friendsListBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <ListRankingItem key={index}>
          <UserMiniCard
            avatarSrc={friend.profile_pic}
            avatarSize='smaller'
            username={friend.username}
            nameFontSize='var(--font-size-small)'
            nameColor='var(--color-light-gray)'
            info={[friend.rating, formatPercentage(friend.total_return)]}
          />
        </ListRankingItem>
      )
    })
  }
  console.log(listRanking)
  return (
    <>
      <ListHeader>
        <SmallCaps><span>N. </span>Player</SmallCaps>
        <SmallCaps>Score | Avg. Return</SmallCaps>
      </ListHeader>
      <ListRankingWrapper>
        {listRanking.length > 0 && friendsListBuilder(listRanking)}
      </ListRankingWrapper>
    </>
  )
}

export { ListGlobalRanking }
