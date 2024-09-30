const { Events } = require('discord.js');
const { getDb } = require('../../helpers/mongodb');
const fetch = require('node-fetch'); // Ensure you have this if not already

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isModalSubmit()) {
            console.log(`Modal submitted with customId: ${interaction.customId}`);
            console.log('1')
            if (interaction.customId === 'userLogin') {
                // Get the user's input from the modal
                const username = interaction.fields.getTextInputValue('login-username');
                const password = interaction.fields.getTextInputValue('login-password');

                try {
                    // Defer reply to avoid the 3-second timeout
                    await interaction.deferReply({ ephemeral: true });

                    const response = await fetch('http://127.0.0.1:5000/user/login', {
                        method: 'POST',
                        headers: {
                            'X-API-KEY': 'divyanshjindal',
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error('HTTP error ' + response.status);
                    }

                    const data = await response.json();
                    const userDB = getDb().collection('discord');
                    const token = data.token;
                    const userid = interaction.user.id;

                    await userDB.updateOne(
                        { userid: userid },
                        { $set: { tokens: token } },
                        { upsert: true }
                    );

                    // Edit the deferred reply with the success message
                    await interaction.editReply({
                        content: `Successfully logged into \`${username}\`.`,
                    });
                } catch (error) {
                    console.error('Error: ', error);
                    await interaction.editReply({
                        content: 'Failed to log in. Please try again.',
                    });
                }
            };
            console.log('2')
            if (interaction.customId === 'userCreate') {
                console.log('yes');
                await interaction.deferReply({ ephemeral: true });
                await interaction.editReply('Done');
                // // Get the user's input from the modal
                // const username = interaction.fields.getTextInputValue('create-username');
                // const password = interaction.fields.getTextInputValue('create-password');
                // const email = interaction.fields.getTextInputValue('create-email');

                // try {
                //     // Defer reply to avoid the 3-second timeout
                //     await interaction.deferReply({ ephemeral: true });

                //     const response = await fetch('http://127.0.0.1:5000/user/create', {
                //         method: 'POST',
                //         headers: {
                //             'X-API-KEY': 'divyanshjindal',
                //             'Content-Type': 'application/json',
                //         },
                //         body: JSON.stringify({
                //             username: username,
                //             password: password,
                //             email: email,
                //         }),
                //     });

                //     if (!response.ok) {
                //         console.log('error');
                //         await interaction.editReply('Error');
                //         throw new Error('HTTP error ' + response.status);
                //     };

                //     const data = await response.json();

                //     // Edit the deferred reply with the success message
                //     await interaction.editReply('Successfully created the user. Now login into it.');
                // } catch (error) {
                //     console.error('Error: ', error);
                //     await interaction.editReply({
                //         content: 'Failed to create user. Please try again.',
                //     });
                // }
            }
            console.log('3')
        }
    else {
        console.log('yesss');
    }
    },
};
