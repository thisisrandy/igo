import React from "react";
import { useSelector } from "react-redux";
import { clearMessage } from "../actions";
import { MESSAGE } from "../constants/StateKeys";
import { GAME } from "../constants/ReducerKeys";
import MessageBase from "./MessageBase";

function Message({ zIndex }) {
  const { [MESSAGE]: message } = useSelector((state) => state[GAME]);

  return (
    <MessageBase
      zIndex={zIndex}
      isOpen={message != null && message !== ""}
      title={"Message"}
      buttonText={"Okay"}
      clickAction={clearMessage}
    >
      {message}
    </MessageBase>
  );
}

export default Message;
