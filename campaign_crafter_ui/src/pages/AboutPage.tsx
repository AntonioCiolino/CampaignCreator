import React from 'react';
import './AboutPage.css'; // We'll create this later if needed

const AboutPage: React.FC = () => {
  return (
    <div className="about-page-container">
      <h1>About Campaign Crafter</h1>
      <p>
        Welcome to Campaign Crafter! This application is designed to help you create, manage,
        and bring your campaign worlds to life. Whether you're a game master, a writer, or
        a world-builder, Campaign Crafter provides tools to streamline your creative process.
      </p>
      <h2>Features</h2>
      <ul>
        <li>Campaign organization</li>
        <li>Character management (Coming Soon!)</li>
        <li>World-building utilities</li>
        <li>Integration with AI for content generation</li>
        <li>Export and share your creations</li>
      </ul>
      <p>
        Our goal is to provide a flexible and powerful platform for all your campaign
        creation needs. We are constantly working on new features and improvements.
      </p>
      <p>
        Thank you for using Campaign Crafter!
      </p>
    </div>
  );
};

export default AboutPage;
