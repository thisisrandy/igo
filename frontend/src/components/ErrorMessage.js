import React from "react";
import { useSelector } from "react-redux";
import { clearError } from "../actions";
import { ERROR_MESSAGE } from "../constants/StateKeys";
import { GAME } from "../constants/ReducerKeys";
import MessageBase from "./MessageBase";

function ErrorMessage({ zIndex }) {
  const { [ERROR_MESSAGE]: message } = useSelector((state) => state[GAME]);

  return (
    <MessageBase
      zIndex={zIndex}
      isOpen={message != null && message !== ""}
      title={"Error"}
      buttonText={"Dismiss"}
      clickAction={clearError}
    >
      The game server encountered an error: "{message}". This is likely because
      it is having connectivity issues with the underlying database, which
      should be remedied shortly. Please wait a while and try again
    </MessageBase>
  );
}

export default ErrorMessage;
