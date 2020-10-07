import React, { useEffect, useState } from 'react'
import { apiPost } from 'components/functions/api'
import { PlayerRow } from 'components/lists/PlayerRow'
import { SmallCaps } from 'components/textComponents/Text'
import styled from 'styled-components'
import { formatPercentage, numberToOrdinal } from 'components/functions/formattingHelpers'
import { ElementTooltip } from 'components/ui/ElementTooltip'
import { PlayerCard } from 'components/ui/cards/PlayerCard'

const ListRankingWrapper = styled.ol`
  font-size: var(--font-size-small);
  padding-inline-start: 30px;
`

const ListRankingItem = styled.li`
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
  const listBuilder = (data) => {
    return data.map((player, index) => {
      const isFriend = listFriends.length > 0 && listFriends.findIndex((row) => {
        return row.id === player.user_id
      })
      const isMarketIndex = player.user_id === null
      const threeMonthReturn = formatPercentage(player.three_month_return, 2)

      const playerCardInfo = [
        { type: 'Games Played', value: player.n_games },
        { type: 'Rating', value: player.rating },
        { type: 'Avg. return', value: threeMonthReturn }
      ]

      return (
        <ListRankingItem key={index}>
          <ElementTooltip
            placement='left'
            message={(
              <PlayerCard
                profilePic={player.profile_pic}
                username={player.username}
                leaderboardPosition={numberToOrdinal(index + 1)}
                isFriend={isFriend !== -1}
                isMarketIndex={isMarketIndex}
                playerStats={playerCardInfo}
              />
            )}
          >
            <PlayerRow
              avatarSrc={player.profile_pic}
              avatarSize='24px'
              username={player.username}
              isMarketIndex={isMarketIndex}
              isFriend={isFriend !== -1}
              isCurrentPlayer=''
              nameFontSize='var(--font-size-small)'
              nameColor='var(--color-light-gray)'
              info={[player.rating, threeMonthReturn]}
            />
          </ElementTooltip>
        </ListRankingItem>
      )
    })
  }
  console.log(listRanking)
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
