import { configureStore } from '@reduxjs/toolkit';
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { combineReducers } from '@reduxjs/toolkit';

import fileProcessingReducer from './slices/fileProcessingSlice';
import validationReducer from './slices/validationSlice';
import userPreferencesReducer from './slices/userPreferencesSlice';
import notificationReducer from './slices/notificationSlice';
import { apiMiddleware } from './middleware/apiMiddleware';

// Persist configuration
const persistConfig = {
  key: 'healthcare-preauth-root',
  storage,
  whitelist: ['userPreferences'], // Only persist user preferences
};

// Root reducer
const rootReducer = combineReducers({
  fileProcessing: fileProcessingReducer,
  validation: validationReducer,
  userPreferences: userPreferencesReducer,
  notifications: notificationReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        ignoredActionsPaths: [
          'payload.timestamp',
          'payload.startTime',
          'payload.endTime',
          'meta.startedTimeStamp',
        ],
        ignoredPaths: [
          'notifications.history.timestamp',
          'validation.validationHistory.timestamp',
          'userPreferences.recentValidationSets.lastUsed',
        ],
      },
    })
    .concat(apiMiddleware.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

export const persistor = persistStore(store);

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;