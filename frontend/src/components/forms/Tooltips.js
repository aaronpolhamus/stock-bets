import React from "react";
import { Popover, OverlayTrigger } from "react-bootstrap";
import { HelpCircle } from "react-feather";

const Tooltip = ({ message }) => (
  <OverlayTrigger
    placement="top"
    trigger="hover"
    overlay={
      <Popover>
        <Popover.Content>{message}</Popover.Content>
      </Popover>
    }
  >
    <HelpCircle size={14} style={{ marginTop: "2px" }} />
  </OverlayTrigger>
);

export { Tooltip };
