const { Events } = require('discord.js');
const { getDb } = require('../../helpers/mongodb');
const fetch = require('node-fetch'); // Ensure you have this if not already

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isModalSubmit()) {
            if (interaction.customId === 'forgotPassword') {
                // Get the user's input from the modal
                const username = interaction.fields.getTextInputValue('forgot-username');
                const email = interaction.fields.getTextInputValue('forgot-email');

                try {
                    // Defer reply to avoid the 3-second timeout
                    await interaction.deferReply({ ephemeral: true });

                    const response = await fetch('http://127.0.0.1:5000/user/forgot-password', {
                        method: 'POST',
                        headers: {
                            'X-API-KEY': 'divyanshjindal',
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            email: email,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error('HTTP error ' + response.status);
                    }

                    // Edit the deferred reply with the success message
                    await interaction.editReply({
                        content: `OTP Successfully sent to your email. Please input the OTP you received in \`user verify-otp\``,
                    });
                } catch (error) {
                    console.error('Error: ', error);
                    await interaction.editReply({
                        content: 'Failed to send OTP. Invalid email or username.',
                    });
                }
            }
        }
    },
};
