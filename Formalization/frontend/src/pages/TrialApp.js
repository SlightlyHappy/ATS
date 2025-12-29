import React from 'react';
import FullApp from './FullApp';

const TrialApp = () => {
  // Trial users get the full app with restrictions handled by context
  // The restrictions are enforced in the components themselves
  return <FullApp />;
};

export default TrialApp;
