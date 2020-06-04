import React, { useEffect, useState } from "react";
import { fetchData } from "components/functions/api";
import { UserMiniCard } from "components/users/UserMiniCard";
import { Header } from "components/layout/Layout";
import { SectionTitle } from "components/textComponents/Text";
import styled from "styled-components";

const FriendsListWrapper = styled.div`
  margin-top: var(--space-300);
`;

const FriendsListList = styled.ul`
  list-style-type: none;
  padding: 0;
`;

const FriendsListItem = styled.li`
  padding: var(--space-100) 0;
`;

const FriendsList = () => {
  const [friendsData, setFriendsData] = useState({});

  useEffect(() => {
    const getFriendsList = async () => {
      const data = await fetchData("get_list_of_friends");
      setFriendsData(data);
    };
    getFriendsList();
  }, []);

  console.log(friendsData, friendsData.length);

  const friendsListBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <FriendsListItem>
          <UserMiniCard
            key={index}
            avatarSrc={friend.profile_pic}
            avatarSize="small"
            username={friend.username}
            nameFontSize="var(--font-size-small)"
            nameColor="var(--color-light-gray)"
          />
        </FriendsListItem>
      );
    });
  };

  return (
    <FriendsListWrapper>
      <Header>
        <SectionTitle color="var(--color-primary)">Friends</SectionTitle>
      </Header>
      <FriendsListList>
        {friendsData.length && friendsListBuilder(friendsData)}
      </FriendsListList>
    </FriendsListWrapper>
  );
};

export { FriendsList };
