import React, { useEffect, useState } from "react";
import { fetchData } from "components/functions/api";
import { UserMiniCard } from "components/users/UserMiniCard";
import { Button, Modal } from "react-bootstrap";
import { Header } from "components/layout/Layout";
import { SectionTitle } from "components/textComponents/Text";
import styled from "styled-components";

const FriendsListWrapper = styled.div`
  margin-top: var(--space-400);
`;

const FriendsListList = styled.ul`
  list-style-type: none;
  padding: 0;
`;

const FriendsListItem = styled.li`
  padding: var(--space-100) 0;
`;

const FriendRequest = styled.p`
  font-size: var(--font-size-small);
  display: flex;
  justify-content: space-between;
`;

const FriendsList = () => {
  const [friendsData, setFriendsData] = useState({});
  const [friendRequestsData, setFriendRequestsData] = useState({});

  const [show, setShow] = useState(false);
  const [requester, setRequester] = useState("");

  const handleClose = () => setShow(false);
  const handleShow = (requester) => {
    setRequester(requester);
    setShow(true);
  };

  useEffect(() => {
    const getFriendsLists = async () => {
      const friends = await fetchData("get_list_of_friends");
      setFriendsData(friends);

      const friendRequests = await fetchData("get_list_of_friend_invites");
      setFriendRequestsData(friendRequests);
    };

    getFriendsLists();
  }, []);

  const friendsListBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <FriendsListItem key={index}>
          <UserMiniCard
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

  const friendRequestsBuilder = (data) => {
    return data.map((friend, index) => {
      return (
        <FriendRequest key={index}>
          {friend} wants to be friends with you
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleShow(friend)}
          >
            View Request
          </Button>
        </FriendRequest>
      );
    });
  };

  return (
    <FriendsListWrapper>
      <Header>
        <SectionTitle color="var(--color-primary)">Friends</SectionTitle>
      </Header>
      {friendRequestsData.length && friendRequestsBuilder(friendRequestsData)}
      <FriendsListList>
        {friendsData.length && friendsListBuilder(friendsData)}
      </FriendsListList>

      <Modal show={show} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>
            New friend request from
            <strong> {requester}</strong>!
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>{requester} wants to be your friend</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
          <Button variant="primary" onClick={handleClose}>
            Accept
          </Button>
        </Modal.Footer>
      </Modal>
    </FriendsListWrapper>
  );
};

export { FriendsList };
