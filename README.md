<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">♫ Lyrics Video Creator ♫</h3>

  <p align="center">
    Generate a lyrics video without hands.
  </p>

  <p>
 
https://github.com/user-attachments/assets/27c217bf-2c9d-49c7-86a5-4f3d0268446a


  </p>
</div>



<!-- ABOUT THE PROJECT -->
## About The Project

With the rapid proliferation of modern music generation AIs such as Suno AI and Udio, the need to share the music you create continues to grow. When sharing music, adding visual elements such as music videos can make the content more appealing.

This project responds to those needs: with Lyrics Video Creator, you can create videos with lyric subtitles almost automatically in just a few operations. All the user needs to prepare is the music data and the lyrics text. You can use Lyrics Video Creator to make your own music appealing.

<p align="right">(<a href="#readme-top">back to top</a>)</p>





<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Before you use this project, you'll need the following requirements.

* [Music AI](https://music.ai/) API key
* OpenAI API key
* Python >= 3.10
* uv

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/Kogia_sima/lyrics_video_creator.git
   ```
2. Install dependencies
   ```sh
   uv sync
   ```
3. Copy the `.env.template` file and save as `.env`.
4. Enter your API in `.env`
   ```js
   MUSICAI_API_KEY=<Your Music API Key>
   OPENAI_API_KEY=<OpenAI API Key>
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

1. Prepare your music file (mp3) and lyrics file (txt)
2. Align the timings of lyrics
   ```sh
   uv run 02_align_lyrics.py /your/music.mp3 /your/lyrics.txt
   ```
3. Translate the lyrics
   ```sh
   uv run 03_translate_lyrics.py /your/lyrics_aligned.json
   ```
4. Generate a lyrics video
   ```sh
   uv run 04_generate_movie.py /your/music.mp3 /your/lyrics_aligned_translated.json /your/background.jpg
   ```

You can find detailed usage information in the --help option's documentation.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Kogia sima - [@puchikujira9402](https://x.com/puchikujira9402)

Project Link: [https://github.com/Kogia_sima/lyrics_video_creator](https://github.com/Kogia_sima/lyrics_video_creator)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
