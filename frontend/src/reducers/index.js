import { combineReducers } from "redux";
import { persistReducer } from "redux-persist";
import storage from "redux-persist/lib/storage";
import gameReducer from "./game";
import { PAST_GAMES } from "../constants/StateKeys";

const rootPersistConfig = {
  key: "root",
  storage,
  blacklist: ["game"],
};

const gamePersistConfig = {
  key: "game",
  storage,
  whitelist: [PAST_GAMES],
};

const rootReducer = combineReducers({
  game: persistReducer(gamePersistConfig, gameReducer),
});

export default persistReducer(rootPersistConfig, rootReducer);
