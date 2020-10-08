import React, { useEffect, useState, useContext } from 'react'
import { UserContext } from 'Contexts'
import { apiPost } from 'components/functions/api'
import { LeaderboardPlayerRow } from 'components/lists/LeaderboardPlayerRow'
import { SmallCaps } from 'components/textComponents/Text'
import styled from 'styled-components'
import { formatPercentage, numberToOrdinal } from 'components/functions/formattingHelpers'

const ListRankingWrapper = styled.ol`
  font-size: var(--font-size-small);
  padding-inline-start: 30px;
`

const ListRankingItemWrapper = styled.li`
  color: var(--color-text-light-gray);
  cursor: pointer;
  position: relative;
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
  const [listRanking, setListRanking] = useState(null)
  const [listsCompound, setListsCompound] = useState(null)
  const { user } = useContext(UserContext)

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
        setListsCompound(response.friends.concat(response.you_invited).concat(response.they_invited))
      })
  }

  useEffect(() => {
    getListRanking()
    getListFriends()
  }, [])
  const listBuilder = (listRanking) => {
    return listRanking.map((player, index) => {
      let friendStatus = ''

      if (listsCompound) {
        const friendIndex = listsCompound.findIndex(item => {
          return player.user_id === item.id
        })
        friendStatus = friendIndex !== -1 ? listsCompound[friendIndex].label : ''
      }

      if (player.username === user.username) friendStatus = 'is_you'

      const isMarketIndex = player.user_id === null
      const threeMonthReturn = formatPercentage(player.three_month_return, 2)
      const nameColor = friendStatus === 'is_you' ? 'var(--color-primary-lighten)' : 'var(--color-light-gray)'
      const playerCardInfo = [
        { type: 'Games Played:', value: player.n_games },
        { type: 'Rating:', value: player.rating },
        { type: 'Avg. return:', value: threeMonthReturn }
      ]

      return (
        <ListRankingItemWrapper key={index}>
          <LeaderboardPlayerRow
            avatarSrc={player.profile_pic}
            avatarSize='24px'
            username={player.username}
            isMarketIndex={isMarketIndex}
            friendStatus={friendStatus}
            isCurrentPlayer=''
            nameFontSize='var(--font-size-small)'
            nameColor={nameColor}
            info={[player.rating, threeMonthReturn]}
            playerCardInfo={playerCardInfo}
            leaderboardPosition={numberToOrdinal(index + 1)}
          />
        </ListRankingItemWrapper>
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
        {listRanking && listBuilder(listRanking)}
      </ListRankingWrapper>
    </>
  )
}

export { GlobalLeaderboard }
